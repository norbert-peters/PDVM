import React from 'react'
import { Link as RouterLink } from 'react-router-dom'

import { AppBar } from '@material-ui/core'
import { darken } from '@material-ui/core/styles'

import styled from 'styled-components'
//import { themes } from '../pdvmThemes/themes'

import { PdvmButton } from '../pdvmComponents/PdvmButton'
import { PdvmSection } from '../pdvmComponents/PdvmSection'
import { Grid, Row, Col } from './pdvmComponents/PdvmRaster';

const Nav = styled(AppBar)`
background-color: ${props => props.theme.bgColor};
color: ${props => props.theme.color};
`
const Header = styled.h1`
  ${({ theme }) => `
    color: ${darken(theme.palette.primary.main, 0.7)};
    background-color: ${theme.palette.primary.main};
    font-size: 2.5em;
    text-align: center;
    max-width: 1000px;
    margin-left: auto;
    margin-right: auto;
    `}
  `;
     


export const Navbar = () => {
  return (
    <PdvmPage>
    <Grid>
      <Row>
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
                        </Row>
     </Grid>
     </PdvmPage>
  )}
