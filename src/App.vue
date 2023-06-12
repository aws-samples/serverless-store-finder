<script setup>
  // Components
  import StoreFinder from "./components/StoreFinder.vue"
  // Amplify JS library setup
  import { Authenticator } from "@aws-amplify/ui-vue";
  import "@aws-amplify/ui-vue/styles.css"
  import { Amplify } from "aws-amplify"
  Amplify.configure({
    // Authentication (via Amazon Cognito)
    Auth: {
      identityPoolId: import.meta.env.VITE_AMAZON_COGNITO_IDENTITY_POOL_NAME,
      userPoolId: import.meta.env.VITE_AMAZON_COGNITO_USER_POOL_NAME,
      userPoolWebClientId: import.meta.env.VITE_AMAZON_COGNITO_USER_POOL_CLIENT_NAME,
      region: import.meta.env.VITE_AWS_REGION
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
    },
    API: {
      endpoints: [
        {
          name: "storeFinderAPIEndpoint1",
          endpoint: import.meta.env.VITE_APIGATEWAY_ENDPOINT_API1
        },
        {
          name: "storeFinderAPIEndpoint2",
          endpoint: import.meta.env.VITE_APIGATEWAY_ENDPOINT_API2
        }
      ]
    }
  });
</script>
<template>
  <authenticator :login-mechanisms="['email']">
    <template #default="{ signOut }">
      <Menubar>
        hello
        <template #start>
          <i class="pi pi-github" /> Find the code on <a
            href="https://github.com/aws-samples/serverless-store-finder"
            target="_blank"
          >GitHub</a>
        </template>
        <template #end>
          <Button
            label="Sign out"
            icon="pi pi-sign-out"
            icon-pos="left"
            style="margin-left: 10px;"
            @click="signOut"
          />
        </template>
      </Menubar>
      <br>
      <StoreFinder />
    </template>
  </authenticator>
</template>
