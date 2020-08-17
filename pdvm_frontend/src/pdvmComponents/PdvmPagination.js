import React from 'react'
import IconButton from '@material-ui/core/IconButton'
import ArrowBackIosTwoTone from '@material-ui/icons/ArrowBackIos'
import ArrowForwardIosTwoTone from '@material-ui/icons/ArrowForwardIos'

import {PdvmText} from './PdvmText'
import {PdvmPaper} from './PdvmPaper'
import Tooltip from '@material-ui/core/Tooltip';
import { Grid, Row, Col } from '../pdvmComponents/PdvmRaster';



const PdvmPagination = ( props ) => {
  const nextPage = props.nextPage
  const prevPage = props.prevPage
  const pageNumber = props.pagenumber
  const numPages = props.numpages
  const count = props.count
  const art = props.art
  
  return(
    <PdvmPaper>
    <Grid >
      <Row>
        <Col size={1} >
        <Tooltip title="Seite zurück" interactive>
        <IconButton
            color="inherit"
            edge="end"
            onClick={prevPage}
          >
            <ArrowBackIosTwoTone />
          </IconButton>    
          </Tooltip>             
        </Col>
        
        <Col size={4} >
          <PdvmText>Seite {pageNumber} von {numPages} - {count} {art}</PdvmText>
        </Col>
        <Col size={1} >       
        <Tooltip title="Seite vor" interactive>
          <IconButton
            color="inherit"
            edge="end"
            onClick={nextPage}
          >
            <ArrowForwardIosTwoTone />
          </IconButton>
          </Tooltip>
        </Col> 
        </Row>
        </Grid>
        </PdvmPaper>
)}

export default PdvmPagination