import { createApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'  // MDI CSS
import router from './router'
// Alternative import method
import * as labsComponents from 'vuetify/labs/components'

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  labsComponents,
})

const app = createApp(App)
app.use(vuetify)
app.use(createPinia())
app.use(router)
app.mount('#app')


