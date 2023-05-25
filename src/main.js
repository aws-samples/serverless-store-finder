import { createApp } from "vue"
import App from "./App.vue"
import PrimeVue from "primevue/config"

import Card from "primevue/card"
import Panel from "primevue/panel"
import Button from "primevue/button"
import AutoComplete from "primevue/autocomplete"
import Dropdown from "primevue/dropdown";
import Message from "primevue/message";
import ProgressSpinner from 'primevue/progressspinner';
import MenuBar from 'primevue/menubar';
import "primevue/resources/themes/saga-blue/theme.css"
import "primevue/resources/primevue.min.css"
import "primeicons/primeicons.css"

const myApp = createApp(App)

myApp.use(PrimeVue)

myApp.component("Card", Card)
myApp.component("Panel", Panel)
myApp.component("Button", Button)
myApp.component("AutoComplete", AutoComplete)
myApp.component("Dropdown", Dropdown)
myApp.component("Message", Message)
myApp.component("ProgressSpinner", ProgressSpinner)
myApp.component("MenuBar", MenuBar)

myApp.mount('#app')
