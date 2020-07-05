import React from 'react'
import { Link as RouterLink } from 'react-router-dom'

import IconButton from '@material-ui/core/IconButton'
import EditTwoTone from '@material-ui/icons/Edit'
import BusinessTwoTone from '@material-ui/icons/Business'
import { Box } from '@material-ui/core'
import Paper from '@material-ui/core/Paper';
import Tooltip from '@material-ui/core/Tooltip';

export const Post = ({ post, excerpt }) => (
  <Paper className={excerpt ? 'post-excerpt' : 'post'}>
    <Box>
  <Box component="span" display="flex" >
      <Box left="0%" p={0} >
        <h1>{post.title}</h1>
      </Box>
      <Box p={1} >
      {excerpt && (
        <div>
    <Tooltip title="Artikel anzeigen" interactive>
          <IconButton
            color="inherit"
            edge="end"
            component={RouterLink}
            to={`/post/posts/${post.id}`}
          >
            <BusinessTwoTone />
          </IconButton>                 
          </Tooltip>
          <Tooltip title="Artikel ändern" interactive>
          <IconButton
            color="inherit"
            edge="end"
            component={RouterLink}
            to={`/post/postedit/${post.id}`}
          >
            <EditTwoTone />
          </IconButton>                 
          </Tooltip>
        </div>
        )}    
      </Box>
      </Box> 
      </Box>
      
              <Box left="0%" p={0} >       
              <p>{excerpt ? post.body.substring(0, 120)+" ..." : post.body}</p>
      </Box>
      </Paper>
)

