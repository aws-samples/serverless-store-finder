<template>
  <div style="text-align: center;">
    <Panel header="Store Finder">
      <div style="margin: 10px;">
        <Message
          severity="info"
          :closable="true"
        >
          This sample application uses locations of 18 major train stations as UK store locations, and over 112,000 post offices as
          US store locations. Please start by selecting the drop-down. Either allow the browser to locate where you are, or enter text
          into the field.
        </Message>
        <Message
          v-if="errorMessage"
          severity="error"
          :closable="true"
        >
          The site encountered an error ({{ errorMessage }})
        </Message>
        <h2>With thousands of international stores, it is easier than ever to experience our world class service!</h2>
        <Dropdown
          v-model="selectedCountry"
          :options="availableCountries"
          option-label="name"
          placeholder="Select a country"
          style="margin-left: 10px;"
        />
      </div>
      <div style="text-align: center; margin: 40px;">
        <AutoComplete
          v-if="selectedCountry"
          v-model="selectedDeparturePlace"
          force-selection
          :suggestions="suggestedDeparturePlaces"
          option-label="text"
          @complete="returnDeparturePlacesSuggestions($event)"
          @item-select="selectDeparturePlaceSuggestion($event)"
        />
        <Button
          v-if="selectedCountry"
          label="Locate me"
          icon="pi pi-compass"
          icon-pos="right"
          style="margin-left: 10px;"
          @click="handleGeolocationViaBrowser($event)"
        />
      </div>
      <div v-if="((destinationLocations.length > 0) && Object.keys(departureLocation).length > 0)">
        <p v-if="selectedDeparturePlace">
          Stores near {{ selectedDeparturePlace.text }} ({{ destinationLocations.length }} results)
        </p>
        <p v-else-if="Object.keys(departureLocation).length > 0">
          Stores near you ({{ destinationLocations.length }} results)
        </p>
      </div>
      <div v-else>
        <ProgressSpinner v-if="awaitingAPIResponse" />
      </div>
      <div
        v-if="destinationLocations.length > 0"
        style="display: flex; gap: 10px; flex-wrap: wrap; width: 100%; text-align: center;"
      >
        <Card
          v-for="store in destinationLocations.slice(0, maxResults)"
          v-if="Object.keys(departureLocation).length > 0"
          style="width: 25em; float:none; margin:0 auto;"
        >
          <template #header>
            <img
              :alt="store.name"
              src="../assets/store.jpeg"
              style="width: 100%;"
            >
          </template>
          <template #title>
            {{ store.name }}
          </template>
          <template #content>
            <p v-if="store.Distance">
              <i class="pi pi-car" /> Distance: {{ Math.trunc(store.Distance) }} km
            </p>
            <p v-if="store.DurationSeconds">
              <i class="pi pi-hourglass" /> Duration: {{ Math.trunc(store.DurationSeconds / 60) }} min by car
            </p>
            <p v-if="store.hours">
              <i class="pi pi-clock" /> Opening hours: {{ store.hours }}
            </p>
            <p v-if="store.address">
              <i class="pi pi-directions" /> {{ store.address }}
            </p>
          </template>
        </Card>
      </div>
      <div
        id="map"
        style="margin-top: 40px; height: 80vh;"
      />
    </Panel>
  </div>
</template>

<script>
  // AWS Amplify Geo and maplibre-gl libraries
  import { createMap } from "maplibre-gl-js-amplify";
  import { Geo, API, Auth } from "aws-amplify";
  import maplibregl from "maplibre-gl";
  import "maplibre-gl/dist/maplibre-gl.css"
  import axios from "axios";

  export default {
    name: "StoreFinder",
    data() {
      return {
        // Amplify geo objects
        map: "",
        geo: "",
        location: "",
        errorMessage: "", // Error messages are shown at the top of the screen
        apiEndpoint: "",
        maxResults: import.meta.env.VITE_MAX_RESULTS_DEFAULT,
        selectedCountry: "",
        availableCountries: [
          {name: "United Kingdom", code: "GBR"},        // API1
          {name: "United States", code: "USA"}          // API2
        ],
        // Map markers
        departureMarker: "",
        destinationMarkers: [],
        selectedDeparturePlace: "",
        suggestedDeparturePlaces: [],
        departureLocation: {},
        destinationLocations: [],
        // Are we waiting for an API response?
        awaitingAPIResponse: false,
        apiToken: ""
      }
    },
    watch: {
      departureLocation: {
        handler(newDepartureLocation) {
          if (Object.keys(newDepartureLocation).length !== 0) {
            this.displayDepartureLocationMarker(this, newDepartureLocation)
            this.returnNearestStores()
          } else {
            if (this.departureMarker !== "") {
              this.departureMarker.remove()
            }
          }
        },
        deep: true
      },
      destinationLocations: {
        handler(newDestinationLocations) {
          this.displayDestinationLocationMarkers(this, newDestinationLocations)
        },
        deep: true
      },
      selectedCountry: {
        handler(newSelectedCountry) {
          if (newSelectedCountry.code === "GBR") {
            this.apiEndpoint = import.meta.env.VITE_APIGATEWAY_ENDPOINT_API1
            this.returnAllStores()
            this.map.flyTo({
              center: [import.meta.env.VITE_GBR_MAP_CENTER_LONG, import.meta.env.VITE_GBR_MAP_CENTER_LAT],
              zoom: import.meta.env.VITE_GBR_MAP_ZOOM
            })
          } else if (newSelectedCountry.code === "USA") {
            this.apiEndpoint = import.meta.env.VITE_APIGATEWAY_ENDPOINT_API2
            this.map.flyTo({
              center: [import.meta.env.VITE_USA_MAP_CENTER_LONG, import.meta.env.VITE_USA_MAP_CENTER_LAT],
              zoom: import.meta.env.VITE_USA_MAP_ZOOM
            })
          }
          this.destinationLocations = []
          this.selectedDeparturePlace = ""
          this.departureLocation = {}
        }
      }
    },
    mounted() {
      this.initializeMap()
    },
    methods: {
      handleGeolocationViaBrowser() {
        // Use browser API to return current location.
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(this.updateDepartureLocation);
          this.selectedDeparturePlace = ""
          this.destinationLocations = []
        } else {
          console.log("Geolocation is not supported by this browser.")
        }
      },
      async returnAllStores() {
        let apiName = ""
        if (this.selectedCountry.code === "GBR") {
          apiName = 'storeFinderAPIEndpoint1';
        } else if (this.selectedCountry.code === "USA") {
          apiName = 'storeFinderAPIEndpoint2';
        }
        const path = '';
        const token = await this.getJWTToken()
        const myInit = {
          headers: {
            Authorization: token
          },
          response: true
        };
        await API.get(apiName, path, myInit).then((response) => {
          this.destinationLocations = response.data
        }).catch((error) => {
          console.log(error.message);
          this.errorMessage = error.message
        });
      },
      async returnNearestStores() {
        // Return only the nearest stores using the API endpoint.
        this.destinationLocations = []
        const post_request = {
          "Departure":
            {"Point": [this.departureLocation.longitude, this.departureLocation.latitude]},
          "MaxResults": this.maxResults
        }
        let apiName = ""
        if (this.selectedCountry.code === "GBR") {
          apiName = 'storeFinderAPIEndpoint1';
        } else if (this.selectedCountry.code === "USA") {
          apiName = 'storeFinderAPIEndpoint2';
        }
        const path = '/nearest';
        this.awaitingAPIResponse = true
        const token = await this.getJWTToken()
        this.generateHash(JSON.stringify(post_request)).then(data => {
          const myInit = {
            body: post_request,
            queryStringParameters: {
              hash: data
            },
            headers: {
              Authorization: token
            },
            response: true
          };
          API.post(apiName, path, myInit).then((response) => {
            this.destinationLocations = response.data
            this.awaitingAPIResponse = false
          }).catch((error) => {
            console.log(error.message);
            this.errorMessage = error.message
            this.errorMessage = this.errorMessage
            this.awaitingAPIResponse = false
          });
        });
      },
      updateDepartureLocation(position) {
        // Update the departure location.
        this.departureLocation.latitude = position.coords.latitude
        this.departureLocation.longitude = position.coords.longitude
      },
      async initializeMap() {
        // Display map tiles.
        this.map = await createMap(
          {
            container: "map",
            zoom: 1,
            center: [0, 0]
          }
        );
        this.map.addControl(new maplibregl.NavigationControl(), "top-left");
      },
      displayDepartureLocationMarker(context, departureLocation) {
        // Display departure maker on the map tiles.
        if (context.departureMarker) {
          context.departureMarker.remove()
        }
        context.departureMarker = new maplibregl.Marker({color: "#0000FF"}).setLngLat(
            [departureLocation.longitude, departureLocation.latitude]
        ).addTo(context.map);
        context.map.jumpTo({center: [departureLocation.longitude, departureLocation.latitude]});
      },
      displayDestinationLocationMarkers(context, destinationLocations) {
        // Display destination makers on the map tiles.
        if (context.destinationMarkers) {
          context.destinationMarkers.forEach(function (marker) {
            marker.remove()
          })
          context.destinationMarkers = []
        }
        if (destinationLocations.length > 0) {
          let bounds = new maplibregl.LngLatBounds();
          destinationLocations.forEach(function (location) {
            let marker = new maplibregl.Marker(
                {color: "#FF0000"}).setLngLat([location.location[0], location.location[1]]).setPopup(
                new maplibregl.Popup().setHTML("<b>" + location.name + "</b>")
            )
                .addTo(context.map);
            context.destinationMarkers.push(marker)
            bounds.extend([location.location[0], location.location[1]])
          })
          if (Object.keys(context.departureLocation).length > 0) {
            bounds.extend([context.departureLocation.longitude, context.departureLocation.latitude])
          }
          context.map.fitBounds(bounds, {
            padding: {top: 70, bottom: 50, left: 50, right: 50}
          })
        }
      },
      returnDeparturePlacesSuggestions(text) {
        // Use entered text to return suggestions of placeIds.
        if (text) {
          let countryCode = this.selectedCountry.code
          const searchForSuggestionsOptions = {
            countries: [countryCode]
          }
          Geo.searchForSuggestions(text.query, searchForSuggestionsOptions).then((results) => {
            this.suggestedDeparturePlaces = results
          }).catch((error) => {
            console.log(error)
          })
        }
      },
      selectDeparturePlaceSuggestion() {
        // Used placeId to return the coordinates of selected departure place.
        if (this.selectedDeparturePlace) {
          Geo.searchByPlaceId(this.selectedDeparturePlace.placeId).then(
              (result) => {
                this.departureLocation.latitude = result.geometry.point[1]
                this.departureLocation.longitude = result.geometry.point[0]
              }).catch((error) => {
                console.log(error)
              }
          )
          this.destinationLocations = []
        }
      },
      async generateHash(inputString) {
        // Generate unique hash. Used for caching by Amazon API Gateway.
        const hashBuffer = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(String(inputString)))
        const hashArray = Array.from(new Uint8Array(hashBuffer))
        return hashArray
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");
      },
      async getJWTToken() {
        const token = `${(await Auth.currentSession()).getIdToken().getJwtToken()}`
        return token
      }
    }
  }
</script>
