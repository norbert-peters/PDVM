import React from 'react';
import { ThemeProvider } from 'styled-components';
import { theme } from './theme';
import { PdvmNavbar } from './pdvmComponents/PdvmNavbar';
import { PdvmPage } from './pdvmComponents/PdvmPage';
import { Grid, Row, Col } from './pdvmComponents/PdvmRaster';


import {
  BrowserRouter as Router,
  Switch,
  Route,
  Redirect,
} from 'react-router-dom'
 
import PostRoutes from './pages/PostRoutes'
import DashboardPage from './pages/DashboardPage'

import { ReactQueryDevtools } from 'react-query-devtools'
import { ReactQueryConfigProvider } from "react-query"

const queryConfig = {
  suspense: true,
}



function App() {

  return (
    <ReactQueryConfigProvider config={queryConfig}>
  <ThemeProvider theme={theme}>
    <Router>
      <PdvmPage>
        <div className='App'>
          <Grid>
            <Row>
              <Col size={1}>
               <PdvmNavbar />
              </Col>
            </Row>
            <Row>
              <Col size={1} collapse='xs'>  
                Wir sind nun links
              </Col>
              <Col size={3}>
                <Switch>
                  <Route exact path="/" component={DashboardPage} />
                  <Route path="/post" component={PostRoutes} />
                  <Redirect to="/" />
                </Switch>
              </Col>
              <Col size={1} collapse='xs'>
                Wir sind nun rechts
              </Col>
            </Row>
          </Grid>
        </div>
      </PdvmPage>
    </Router>
    <ReactQueryDevtools initialIsOpen />
  </ThemeProvider>
  </ReactQueryConfigProvider>
  );
}

export default App;