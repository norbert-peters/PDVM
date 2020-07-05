import React from 'react'
import IconButton from '@material-ui/core/IconButton'
import ArrowBackIosTwoTone from '@material-ui/icons/ArrowBackIos'
import ArrowForwardIosTwoTone from '@material-ui/icons/ArrowForwardIos'

import {PdvmText} from './PdvmText'
//import {PdvmFlexBox} from './PdvmFlexBox'
import { Box } from '@material-ui/core'
import Paper from '@material-ui/core/Paper';
import Tooltip from '@material-ui/core/Tooltip';



const PdvmPagination = ( props ) => {
  const nextPage = props.nextPage
  const prevPage = props.prevPage
  const pageNumber = props.pageNumber
  const numPages = props.numPages
  const count = props.count
  const art = props.art
  
  return(
    <Paper>
    <Box component="span" display="flex" marginTop='1em' marginBottom='1em' >
        <Box left="0%" p={1} >
        <Tooltip title="Seite zurück" interactive>
        <IconButton
            color="inherit"
            edge="end"
            onClick={prevPage}
          >
            <ArrowBackIosTwoTone />
          </IconButton>    
          </Tooltip>             
        </Box>
        
        <Box p={2} >
          <PdvmText>Seite {pageNumber} von {numPages} - {count} {art}</PdvmText>
        </Box>
        <Box right="0%" p={1} >       
        <Tooltip title="Seite vor" interactive>
          <IconButton
            color="inherit"
            edge="end"
            onClick={nextPage}
          >
            <ArrowForwardIosTwoTone />
          </IconButton>
          </Tooltip>
        </Box> 
        </Box>
        </Paper>
)}

export default PdvmPagination