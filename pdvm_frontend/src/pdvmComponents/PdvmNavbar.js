import React from 'react'
import { Link as RouterLink } from 'react-router-dom'

import {PdvmMenuThemes} from '../pdvm_menu/PdvmMenuThemes';

import styled from 'styled-components'
import HomeIconTowTon from '@material-ui/icons/Home';

import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import SearchIcon from '@material-ui/icons/Search';

import Drawer from '@material-ui/core/Drawer';
import List from '@material-ui/core/List';
import Divider from '@material-ui/core/Divider';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import {pdvm_artikel} from '../pdvm_menu/pdvm_artikel';
import {pdvm_standard} from '../pdvm_menu/pdvm_standard';
import InboxIcon from '@material-ui/icons/MoveToInbox';
import MailIcon from '@material-ui/icons/Mail';
import PermIdentityTwoTone from '@material-ui/icons/PermIdentityTwoTone'
import ListItemText from '@material-ui/core/ListItemText';
import { Grid, Row, Col } from '../pdvmComponents/PdvmRaster';
import { PdvmNavTitle } from '../pdvmComponents/PdvmNavTitle';
import Tooltip from '@material-ui/core/Tooltip';
import { PdvmIconButton } from './PdvmIconButton';


const Nav = styled(Grid)`
  ${({ theme }) => `
    background-color: ${theme.back.navbar};
    color: ${theme.front.navbar};
    margin-bottom: 0.5em;
  `}
`;

export const PdvmNavbar = (props) => {
    const [opendr, setOpendr] = React.useState(false);
    const [openda, setOpenda] = React.useState(false);

    
    const handleDrawerOpen = () => {
      setOpendr(true);
    };
  
    const handleDrawerClose = () => {
      setOpendr(false);
    };
  
    const handleDrOpen = () => {
      setOpenda(true);
    };
  
    const handleDrClose = () => {
      setOpenda(false);
    };

  return (
    <>
    <Nav >
      <Row>
        <Col size={0.2}>
          <Tooltip title="App Menu" interactive>
      <IconButton
        name='Menu'
        color="inherit"
        aria-label="open drawer"
        onClick={handleDrawerOpen}
        edge="start"
      >
        <MenuIcon />
      </IconButton>
      </Tooltip>
      </Col>
      <Col size={0.5}>
      <PdvmIconButton 
            ttitle = "zum Dashboard" 
            togo = {`/`} 
            nicon = {<HomeIconTowTon />} />
      </Col>
      <Col size={0}></Col>
      <Col size={4} >
      <PdvmNavTitle>
        PDVM System
      </PdvmNavTitle>
      </Col>
      <Col size={0}></Col>
      <Col size={0}>
      <IconButton aria-label="search" color="inherit">
        <SearchIcon />
      </IconButton>
      </Col>
      <Col size={0}>
      {<PdvmMenuThemes />}
      </Col>
      <Col size={0}>
        <Tooltip title="Anwender" interactive >
      <IconButton
        color="inherit"
        aria-label="Person"
        edge="end"
        onClick={handleDrOpen}
      >
        <PermIdentityTwoTone />
       </IconButton>  
       </Tooltip>
       </Col>
      <Col size={1}>
      <Tooltip title="rechtes Menü" interactive>
      <IconButton
        color="inherit"
        aria-label="open dr"
        edge="end"
        onClick={handleDrOpen}
      >
        <MenuIcon />
       </IconButton>  
       </Tooltip>
       </Col>
       </Row>               
    </Nav>
    <Drawer
      variant="persistent"
      anchor="left"
      open={opendr}
    >
      <div > 
        <IconButton name='Menu' onClick={handleDrawerClose}>
          <ChevronLeftIcon />
        </IconButton>
      </div>
      <Divider />
      <List>
        {pdvm_artikel().pdvm_item.map((artikel, index) => (
          <ListItem 
            button key={artikel.id} 
            component={RouterLink} 
            to={artikel.url}
            onClick={handleDrawerClose}
          >
            <ListItemIcon >
              {index % 2 === 0 ? <InboxIcon /> : <MailIcon />}
            </ListItemIcon>
            <ListItemText primary={artikel.name} />
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        {pdvm_standard().pdvm_item.map((standard, index) => (
          <ListItem 
            button key={standard.id} 
            component={RouterLink} 
            to={standard.url}
            onClick={handleDrawerClose}
          >
            <ListItemIcon>{index % 2 === 0 ? <InboxIcon /> : <MailIcon />}</ListItemIcon>
            <ListItemText primary={standard.name} />
          </ListItem>
        ))}
      </List>
    </Drawer>
    <Drawer
      variant="persistent"
      anchor="right"
      open={openda}
    >
      <div >
        <IconButton onClick={handleDrClose}>
          <ChevronLeftIcon />
        </IconButton>
      </div>
      <Divider />
      <List>
        {['Inbox', 'Starred', 'Send email', 'Drafts'].map((text, index) => (
          <ListItem button key={text}>
            <ListItemIcon>{index % 2 === 0 ? <InboxIcon /> : <MailIcon />}</ListItemIcon>
            <ListItemText primary={text} />
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        {['All mail', 'Trash', 'Spam'].map((text, index) => (
          <ListItem button key={text}>
            <ListItemIcon>{index % 2 === 0 ? <InboxIcon /> : <MailIcon />}</ListItemIcon>
            <ListItemText primary={text} />
          </ListItem>
        ))}
      </List>
    </Drawer>
  </>
)}
