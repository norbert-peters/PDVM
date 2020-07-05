import React, {useState} from 'react'
import {
  BrowserRouter as Router,
  Switch,
  Route,
  Redirect,
} from 'react-router-dom'
import { Link as RouterLink } from 'react-router-dom'
 
import {ThemeProvider} from 'styled-components'
import {selectedTheme} from './components/Global'
import { 
  StylesProvider,
} from '@material-ui/core/styles';
import PostRoutes from './pages/PostRoutes'
import DashboardPage from './pages/DashboardPage'
import { AppBar } from '@material-ui/core'
import MenuItem from '@material-ui/core/MenuItem';
import Menu from '@material-ui/core/Menu';
import { ThemeProvider as MuiThemeProvider } from '@material-ui/core'

import Toolbar from '@material-ui/core/Toolbar';
import IconButton from '@material-ui/core/IconButton';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core/styles';
import MenuIcon from '@material-ui/icons/Menu';
import SearchIcon from '@material-ui/icons/Search';
import MoreIcon from '@material-ui/icons/MoreVert';
import Paper from '@material-ui/core/Paper';

import PropTypes from 'prop-types';
import CssBaseline from '@material-ui/core/CssBaseline';
import useScrollTrigger from '@material-ui/core/useScrollTrigger';
import clsx from 'clsx';
import Drawer from '@material-ui/core/Drawer';
import List from '@material-ui/core/List';
import Divider from '@material-ui/core/Divider';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import InboxIcon from '@material-ui/icons/MoveToInbox';
import MailIcon from '@material-ui/icons/Mail';
import HomeIcon from '@material-ui/icons/Home';

import {pdvm_artikel} from './pdvm_menu/pdvm_artikel'
import {pdvm_standard} from './pdvm_menu/pdvm_standard'



function ElevationScroll(props) {
  const { children } = props;
  const trigger = useScrollTrigger({
    disableHysteresis: true,
    threshold: 0,
  });

  return React.cloneElement(children, {
    elevation: trigger ? 4 : 0,
  });
}

ElevationScroll.propTypes = {
  children: PropTypes.element.isRequired,
};

  function getMuiTheme(pdvmThemeType) {
    return selectedTheme(pdvmThemeType);
  }; 

const drawerWidth = 240;   // beide Seiten gleich

const useStyles = makeStyles((theme) => ({
  paper: {
    padding: theme.spacing(2),
    textAlign: 'left',
    color: theme.palette.text.secondary,
  },  
  root: {
    display: 'flex',
  },
  appBar: {
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
  },
  appBarShift: {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: drawerWidth,
    transition: theme.transitions.create(['margin', 'width'], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  },
  menuButton: {
    marginRight: theme.spacing(2),
  },
  hide: {
    display: 'none',
  },
  drawer: {
    width: drawerWidth,
    flexShrink: 0,
  },
  drawerPaper: {
    width: drawerWidth,
  },
  drawerHeader: {
    display: 'flex',
    alignItems: 'center',
    padding: theme.spacing(0, 1),
    // necessary for content to be below app bar
    ...theme.mixins.toolbar,
    justifyContent: 'flex-end',
  },
  content: {
    flexGrow: 1,
    padding: theme.spacing(3),
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.sharp,
      duration: theme.transitions.duration.leavingScreen,
    }),
    marginLeft: -drawerWidth,
    marginRight: -drawerWidth,
  },
  contentShift: {
    transition: theme.transitions.create('margin', {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  },
}));

const App = () => {
  console.log(pdvm_artikel())
  const [theme, setTheme] = useState(getMuiTheme('common'))
  const [anchorEl, setAnchorEl] = React.useState(null);
  const classes = useStyles();
  const [opendr, setOpendr] = React.useState(false);
  const [openth, setOpenth] = React.useState(false);
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

  const handleMenu = (event) => {
    setOpenth(true)
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setOpenth(false)
    setAnchorEl(null);
  };

  return (
    <StylesProvider injectFirst>
      <MuiThemeProvider theme={theme}>
        <ThemeProvider theme={theme}>
          {console.log(theme)}
              <Router>
              <div className={classes.root}>
                <CssBaseline />
                <AppBar
                  position="fixed"
                  className={clsx(classes.appBar, {
                    [classes.appBarShift]: opendr,
                  })}
                >
                  <Toolbar >
                  <IconButton
                  name='Menu'
                  color="inherit"
                  aria-label="open drawer"
                  onClick={handleDrawerOpen}
                  edge="start"
                  className={clsx(classes.menuButton, opendr && classes.hide)}
                >
                  <MenuIcon />
                </IconButton>
                  <IconButton
                    name="Dashboard"
                    aria-label="account of current user"
                    aria-controls="menu-appbar"
                    aria-haspopup="true"
                    component={RouterLink} 
                    to="/"
                    color="inherit"
                  >
                    <HomeIcon />
                  </IconButton>   
                  <Typography variant="h5" noWrap direction="center">
                    PDVM System
                  </Typography>
                  <IconButton aria-label="search" color="inherit">
                    <SearchIcon />
                  </IconButton>
                  <IconButton
                    name="themeMenu"
                    aria-label="account of current user"
                    aria-controls="menu-appbar"
                    aria-haspopup="true"
                    onClick={handleMenu}
                    color="inherit"
                  >
                    <MoreIcon />
                  </IconButton>    
                  <IconButton
            color="inherit"
            aria-label="open dr"
            edge="end"
            onClick={handleDrOpen}
            className={clsx(openda && classes.hide)}
          >
            <MenuIcon />
          </IconButton>                 
        </Toolbar>
        <Menu
                    id="menu-appbar"
                    variant="persistent"
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
                    open={openth}
                    onClose={handleClose}
                  >
                    <MenuItem name='themeManu' onClick={() =>{setTheme(getMuiTheme('common'));handleClose()}} >Thema Start</MenuItem>
                    <MenuItem name='themeManu' onClick={() =>{setTheme(getMuiTheme('light'));handleClose()}} >Thema Default</MenuItem>
                    <MenuItem name='themeManu' onClick={() =>{setTheme(getMuiTheme('dark'));handleClose()}} >Thema Extra</MenuItem>
                  </Menu>
      </AppBar>
      <Drawer
        className={classes.drawer}
        variant="persistent"
        anchor="left"
        open={opendr}
        classes={{
          paper: classes.drawerPaper,
        }}
      >
        <div className={classes.drawerHeader}> 
          <IconButton name='Menu' onClick={handleDrawerClose}>
            {theme.direction === 'ltr' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
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
      <main
        className={clsx(classes.content, {
          [classes.contentShift]: opendr,
        })}
      >
        <Paper className={classes.paper} >
          <Switch>
            <Route exact path="/" component={DashboardPage} />
            <Route path="/post" component={PostRoutes} />
            <Redirect to="/" />
          </Switch>
        </Paper>
      </main>
      <Drawer
        className={classes.drawer}
        variant="persistent"
        anchor="right"
        open={openda}
        classes={{
          paper: classes.drawerPaper,
        }}
      >
        <div className={classes.drawerHeader}>
          <IconButton onClick={handleDrClose}>
            {theme.direction === 'rtl' ? <ChevronLeftIcon /> : <ChevronRightIcon />}
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
    </div>
              </Router>
        </ThemeProvider>
      </MuiThemeProvider>
    </StylesProvider>
  )
} 

export default App
