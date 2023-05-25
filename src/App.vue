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
      identityPoolId: import.meta.env.VITE_AMAZON_COGNITO_IDENTITY_POOL_ID,
      userPoolId: import.meta.env.VITE_AMAZON_COGNITO_USER_POOL_ID,
      userPoolWebClientId: import.meta.env.VITE_AMAZON_COGNITO_USER_POOL_WEB_CLIENT_ID,
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
    }
  });
</script>
<template>
  <authenticator>
    <template v-slot="{ user, signOut }">
      <Menubar>
        <div style="text-align: right">
          <div style="margin: 10px">
            <Button
                label="Sign out"
                icon="pi pi-sign-out"
                icon-pos="left"
                style="margin-left: 10px;"
                @click="signOut"
            />
          </div>
        </div>
      </Menubar>
      <StoreFinder />
    </template>
  </authenticator>
</template>
