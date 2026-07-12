import React from "react"
import ReactDOM from "react-dom/client"
import { HashRouter } from "react-router-dom"
import { ColorModeScript } from "@chakra-ui/react"
import App from "./App.jsx"
import theme from "theme/theme"

const root = ReactDOM.createRoot(document.getElementById("root"))

root.render(
  <>
    <ColorModeScript initialColorMode={theme.config.initialColorMode} />
    <HashRouter>
      <App />
    </HashRouter>
  </>
)
