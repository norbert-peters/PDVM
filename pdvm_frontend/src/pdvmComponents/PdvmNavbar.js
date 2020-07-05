import React, {useState} from 'react'
import { Link as RouterLink } from 'react-router-dom'

import { AppBar } from '@material-ui/core'
import { darken } from '@material-ui/core/styles'
import {selectedTheme} from '../components/Global'
import MenuItem from '@material-ui/core/MenuItem';
import Menu from '@material-ui/core/Menu';


import styled from 'styled-components'
//import { themes } from '../pdvmThemes/themes'

import { PdvmButton } from '../pdvmComponents/PdvmButton'
import { PdvmSection } from '../pdvmComponents/PdvmSection'

import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import MenuIcon from '@material-ui/icons/Menu';
import SearchIcon from '@material-ui/icons/Search';
import MoreIcon from '@material-ui/icons/MoreVert';
import Paper from '@material-ui/core/Paper';
import Grid from '@material-ui/core/Grid';

import PropTypes from 'prop-types';
import CssBaseline from '@material-ui/core/CssBaseline';
import useScrollTrigger from '@material-ui/core/useScrollTrigger';
import Box from '@material-ui/core/Box';
import Container from '@material-ui/core/Container';


const Nav = styled(AppBar)`
background-color: ${props => props.theme.bgColor};
color: ${props => props.theme.color};
`
function ElevationScroll(props) {
    const { children, window } = props;
    // Note that you normally won't need to set the window ref as useScrollTrigger
    // will default to window.
    // This is only being set here because the demo is in an iframe.
    const trigger = useScrollTrigger({
      disableHysteresis: true,
      threshold: 0,
      target: window ? window() : undefined,
    });
  
    return React.cloneElement(children, {
      elevation: trigger ? 4 : 0,
    });
  }
  
  ElevationScroll.propTypes = {
    children: PropTypes.element.isRequired,
    /**
     * Injected by the documentation to work in an iframe.
     * You won't need it on your project.
     */
    window: PropTypes.func,
  };
  
  
  const useStyles = makeStyles((theme) => ({
    root: {
      flexGrow: 1,
    },
    paper: {
      padding: theme.spacing(2),
      textAlign: 'center',
      color: theme.palette.text.secondary,
    },
  })); 

  function getMuiTheme(pdvmThemeType) {
    return selectedTheme(pdvmThemeType);
  }; 
   



export const PdvmNavbar = () => {
    const [theme, setTheme] = useState(getMuiTheme('common'))
    const [auth, setAuth] = React.useState(true);
    const [anchorEl, setAnchorEl] = React.useState(null);
    const open = Boolean(anchorEl);
  
    const handleChange = (event) => {
        setAuth(event.target.checked);
      };
    
      const handleMenu = (event) => {
        setAnchorEl(event.currentTarget);
      };
    
      const handleClose = () => {
        setAnchorEl(null);
      };
    
      const classes = useStyles();
    
  return (
    <Box>
                        <Nav static >
                          <Toolbar >
                            <IconButton
                              edge="start"
                              color="inherit"
                              aria-label="open drawer"
                            >
                              <MenuIcon />
                            </IconButton>
                            <Typography variant="h5" noWrap>
                              PDVM System
                            </Typography>
                            <PdvmButton pdvmstyle='text' component={RouterLink} to="/">PDVM Dashboard</PdvmButton>
                            <PdvmButton pdvmstyle='text' component={RouterLink} to="/post/posts/">Artikel und Kommentare</PdvmButton>
                            <IconButton aria-label="search" color="inherit">
                              <SearchIcon />
                            </IconButton>
                            <IconButton
                              aria-label="account of current user"
                              aria-controls="menu-appbar"
                              aria-haspopup="true"
                              onClick={handleMenu}
                              color="inherit"
                            >
                              <MoreIcon />
                            </IconButton>                     
                            <Menu
                              id="menu-appbar"
                              anchorEl={anchorEl}
                              anchorOrigin={{
                                vertical: 'top',
                                horizontal: 'right',
                              }}
                              keepMounted
                              transformOrigin={{
                                vertical: 'top',
                                horizontal: 'right',
                              }}
                              PaperProps={{
                                style: {
                                  width: '20ch',
                                  color: 'black',
                                  background: 'yellow',
                                },
                              }}  
                              open={open}
                              onClose={handleClose}
                            >
                              <MenuItem onClick={() =>{setTheme(getMuiTheme('common'));handleClose()}} >Thema Start</MenuItem>
                              <MenuItem onClick={() =>{setTheme(getMuiTheme('light'));handleClose()}} >Thema Default</MenuItem>
                              <MenuItem onClick={() =>{setTheme(getMuiTheme('dark'));handleClose()}} >Thema Extra</MenuItem>
                            </Menu>
                          </Toolbar>
                        </Nav>

     </Box>
  )}
