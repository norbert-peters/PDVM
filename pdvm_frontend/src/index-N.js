import React from 'react'
import { render } from 'react-dom'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'


import App from './App'
import rootReducer from './slices'

//import './index.css'
//import WebFont from 'webfontloader'

/*WebFont.load({
  google: {
    families: ['Roboto:300,500,700']
  }
});
*/


const store = configureStore({ reducer: rootReducer })

render(
  <Provider store={store}>
      <App />
  </Provider>,
  document.getElementById('root')
)
