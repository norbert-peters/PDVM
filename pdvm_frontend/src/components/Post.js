import React from 'react'
import EditTwoTone from '@material-ui/icons/Edit'
import BusinessTwoTone from '@material-ui/icons/Business'
import { Box } from '@material-ui/core'
import { PdvmPaper } from '../pdvmComponents/PdvmPaper';
import { PdvmIconButton } from '../pdvmComponents/PdvmIconButton';

export const Post = ({ post, excerpt }) => (
  <PdvmPaper className={excerpt ? 'post-excerpt' : 'post'}>
    {console.log(post)}
    <Box>
  <Box component="span" display="flex" >
      <Box left="0%" p={0} >
        <h1>{post.title}</h1>
      </Box>
      <Box p={1} >
      {excerpt && (
        <div>
          <PdvmIconButton 
            ttitle = "Artikel anzeigen" 
            togo = {`/post/posts/${post.id}`} 
            nicon = {<BusinessTwoTone />} />
          <PdvmIconButton 
            ttitle = "Artikel ändern" 
            togo = {`/post/postedit/${post.id}/mod`} 
            nicon = {<EditTwoTone />} />
        </div>
        )}    
      </Box>
      </Box> 
      </Box>
      
              <Box left="0%" p={0} >       
              <p>{excerpt ? post.body.substring(0, 120)+" ..." : post.body}</p>
      </Box>
      </PdvmPaper>
)

