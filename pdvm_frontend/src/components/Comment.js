import React from 'react'
import { Link as RouterLink } from 'react-router-dom'

//import { PdvmButton } from '../pdvmComponents/PdvmButton'
import IconButton from '@material-ui/core/IconButton'
import EditTwoTone from '@material-ui/icons/Edit'
import { Box } from '@material-ui/core'
import Paper from '@material-ui/core/Paper';
import Tooltip from '@material-ui/core/Tooltip';


export const Comment = ({ comment }) => (
  <Paper className="comment">
    <Box>
  <Box component="span" display="flex" >
      <Box left="0%" p={0} >
      <h2>{comment.name}</h2>
      </Box>
      <Box p={1} >
    <Tooltip title="Kommentar ändern" interactive>
          <IconButton
            color="inherit"
            edge="end"
            component={RouterLink}
            to={`/post/postsedit/${comment.id}/${comment.postId}`}
          >
            <EditTwoTone />
          </IconButton>                 
          </Tooltip>
          </Box>
          </Box>
    <h3>{comment.email}</h3>
    <p>{comment.body}</p>
    </Box>
  </Paper>
)

