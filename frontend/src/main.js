import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createAuth0 } from '@auth0/auth0-vue'
import App from './App.vue'
import router from './router'
import './styles/global.css'

const app = createApp(App)
const securityProvider = import.meta.env.VITE_SECURITY_PROVIDER || 'auth0'
const oidcIssuer = import.meta.env.VITE_OIDC_ISSUER
const auth0Domain = import.meta.env.VITE_AUTH0_DOMAIN || (oidcIssuer ? new URL(oidcIssuer).host : '')
const auth0ClientId = import.meta.env.VITE_OIDC_CLIENT_ID || import.meta.env.VITE_AUTH0_CLIENT_ID
const auth0Audience = import.meta.env.VITE_OIDC_AUDIENCE || import.meta.env.VITE_AUTH0_AUDIENCE

app.use(createPinia())
if (securityProvider === 'auth0' && auth0Domain && auth0ClientId) {
  app.use(
    createAuth0({
      domain: auth0Domain,
      clientId: auth0ClientId,
      authorizationParams: {
        redirect_uri: window.location.origin,
        ...(auth0Audience ? { audience: auth0Audience } : {}),
      },
      cacheLocation: 'localstorage',
      useRefreshTokens: true,
    })
  )
}
app.use(router)
app.mount('#app')
