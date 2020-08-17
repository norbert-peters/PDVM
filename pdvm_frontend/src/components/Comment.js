import React from 'react'
import { PdvmPaper } from '../pdvmComponents/PdvmPaper'
import EditTwoTone from '@material-ui/icons/Edit'
import { Box } from '@material-ui/core'
import { PdvmIconButton } from '../pdvmComponents/PdvmIconButton';

export const Comment = ({ comment }) => (
  <PdvmPaper >
    <Box>
  <Box component="span" display="flex" >
      <Box left="0%" p={0} >
      <h2>{comment.name}</h2>
      </Box>
      <Box p={1} >
      <PdvmIconButton 
            ttitle = "Kommentar ändern" 
            togo = {`/post/postsedit/${comment.id}/${comment.postId}`} 
            nicon = {<EditTwoTone />} />
          </Box>
          </Box>
    <h3>{comment.email}</h3>
    <p>{comment.body}</p>
    </Box>
  </PdvmPaper>
)

