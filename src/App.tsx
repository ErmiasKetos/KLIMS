import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import { ChakraProvider, Box, VStack, Grid, theme } from "@chakra-ui/react"
import { ColorModeSwitcher } from "./ColorModeSwitcher"
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Requests from './pages/Requests';
import TrayConfigurator from './pages/TrayConfigurator';
import Inventory from './pages/Inventory';
import Production from './pages/Production';
import Shipping from './pages/Shipping';

export const App = () => (
  <ChakraProvider theme={theme}>
    <Router>
      <Box textAlign="center" fontSize="xl">
        <Grid minH="100vh" p={3}>
          <ColorModeSwitcher justifySelf="flex-end" />
          <VStack spacing={8}>
            <Navbar />
            <Switch>
              <Route exact path="/" component={Dashboard} />
              <Route path="/requests" component={Requests} />
              <Route path="/configurator" component={TrayConfigurator} />
              <Route path="/inventory" component={Inventory} />
              <Route path="/production" component={Production} />
              <Route path="/shipping" component={Shipping} />
            </Switch>
          </VStack>
        </Grid>
      </Box>
    </Router>
  </ChakraProvider>
)

