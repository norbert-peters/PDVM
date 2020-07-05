import React from 'react'
import { Link as RouterLink } from 'react-router-dom';
import {PdvmButton} from '../pdvmComponents/PdvmButton'
import Paper from '@material-ui/core/Paper';
import styled from 'styled-components';


const PdvmPaper = styled(Paper)`
    paperColor: '#000';
    background: 'yellow';
`

const DashboardPage = () => (
  <div>
    <br />
    <h1>PDVM Dashboard</h1>
    <p>Hier ist das Dasboard oder später auch die Startseite.</p>
    <PdvmPaper >
      <div>
      <h2 >Artikel und Kommentare</h2>
      </div>
      <PdvmButton display='normaly' component={RouterLink} to="/post/posts/">
        Zeige Artikel
      </PdvmButton>
    </PdvmPaper>
  </div>
)
export default DashboardPage
