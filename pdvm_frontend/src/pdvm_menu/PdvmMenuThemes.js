import React, {useState} from 'react'
import MenuItem from '@material-ui/core/MenuItem';
import Menu from '@material-ui/core/Menu';
import IconButton from '@material-ui/core/IconButton';
import MoreIcon from '@material-ui/icons/MoreVert';
import { Tooltip } from '@material-ui/core';


export const PdvmMenuThemes = (props) => {
  console.log('Themes Menu angekommen')
  console.log(props)
  const [anchorEl, setAnchorEl] = useState(null);
  const [openth, setOpenth] = useState(false);

  const handleClose = () => {
    setOpenth(false)
    setAnchorEl(null);
  };

  const handleMenu = (event) => {
        setOpenth(true)
        setAnchorEl(event.currentTarget);
      };
    
    

  return(
    <>
    <Tooltip title="Theme Menü"  interactive >
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
  </Tooltip> 

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
      width: '20em',
      color: 'black',
      background: 'yellow',
    },
  }}  
  open={openth}
  onClose={handleClose}
>
<MenuItem name='themeMenu' onClick={() =>{handleClose()}} >Thema Start</MenuItem>
<MenuItem name='themeMenu' onClick={() =>{handleClose()}} >Thema Default</MenuItem>
<MenuItem name='themeMenu' onClick={() =>{handleClose()}} >Thema Extra</MenuItem>
</Menu>
</>
)
}