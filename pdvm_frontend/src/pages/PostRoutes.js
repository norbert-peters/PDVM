import React from 'react'
import {
  Switch,
  Route,
} from 'react-router-dom'

import EditCommentPage from './EditCommentPage'
import EditPostPage from './EditPostPage'
import PostsPage from './PostsPage'
import SinglePostPage from './SinglePostPage'



const PostRoutes = () => {
  return (
      <Switch>
        <Route exact path="/post/posts/" component={PostsPage} />
        <Route exact path="/post/posts/:id" component={SinglePostPage} />
        <Route exact path="/post/postsedit/:id/:postId/:pdvm" component={EditCommentPage} />
        <Route exact path="/post/postedit/:id/:pdvm" component={EditPostPage} />
      </Switch>
  )
}

export default PostRoutes
