<script setup>
  // Components
  import StoreFinder from "./components/StoreFinder.vue"
  // Amplify JS library setup
  import { Amplify } from "aws-amplify"
  Amplify.configure({
    // Authentication (via Amazon Cognito)
    Auth: {
      identityPoolId: import.meta.env.VITE_AMAZON_COGNITO_IDENTITY_POOL_ID,
      region: import.meta.env.VITE_AWS_REGION,
    },
    // Amazon Location Service
    geo: {
      AmazonLocationService: {
        maps: {
          items: {
            [import.meta.env.VITE_AMAZON_LOCATION_SERVICE_MAP]: {
              style: "Default style"
            },
          },
          default: import.meta.env.VITE_AMAZON_LOCATION_SERVICE_MAP,
        },
        search_indices: {
          items: [import.meta.env.VITE_AMAZON_LOCATION_SERVICE_PLACES_INDEX],
          default: import.meta.env.VITE_AMAZON_LOCATION_SERVICE_PLACES_INDEX
        },
        region: import.meta.env.VITE_AWS_REGION,
      },
    }
  });
</script>
<template>
  <StoreFinder />
</template>
