import React from 'react'
import { Link as RouterLink } from 'react-router-dom';
import {PdvmButton} from '../pdvmComponents/PdvmButton'
import {PdvmPaper} from '../pdvmComponents/PdvmPaper'


const DashboardPage = () => (
  <div>
    <br />
    <h1>PDVM Dashboard</h1>
    <p>Hier ist das Dasboard oder später auch die Startseite.</p>
    <PdvmPaper >
      <div>
      <h2 >Artikel und Kommentare</h2>
      </div>
      <RouterLink to="/post/posts/">
        <PdvmButton >
          Zeige Artikel
        </PdvmButton>
      </RouterLink>
    </PdvmPaper>
  </div>
)
export default DashboardPage
