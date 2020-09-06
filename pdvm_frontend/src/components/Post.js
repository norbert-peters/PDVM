import React from 'react'
import EditTwoTone from '@material-ui/icons/Edit'
import BusinessTwoTone from '@material-ui/icons/Business'
import { Box } from '@material-ui/core'
import { PdvmPaper } from '../pdvmComponents/PdvmPaper';
import  PdvmInputControl  from '../pdvmComponents/PdvmInputControl'
import { PdvmHeader } from '../pdvmComponents/PdvmHeader'

function myButton(post) {  
  return [
  {
    'id': 0,
    'ttitle' : "Artikel anzeigen", 
    'togo' : `/post/posts/${post.id}`, 
    'nicon' : <BusinessTwoTone />,
  },
  {
    'id': 1,
    'ttitle' : "Artikel ändern", 
    'togo' : `/post/postedit/${post.id}/mod`, 
    'nicon' : <EditTwoTone />,
  },
]
}

export const Post = ({ post, excerpt }) => (
  <PdvmPaper className={excerpt ? 'post-excerpt' : 'post'} >
    <PdvmHeader
      phKey={post.id}
      phType='h1'
      phTitle={post.title}
      phButton={myButton(post)}
      phPost={post}
      phExcerpt={excerpt}
    />
    <Box left="0%" p={0} >       
      {excerpt ?
        <PdvmInputControl
          pdvmType = 'readonly'
          type = 'text'
          value={post.body.substring(0, 120)+" ..."}
        />
      :
        <PdvmInputControl
          pdvmType = 'readonly'
          type = 'text'
          value= {post.body}
        />
      }
    </Box>
  </PdvmPaper>
)
