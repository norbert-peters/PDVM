import { combineReducers } from 'redux'

import postsReducer from './posts'
import postReducer from './post'
import commentsReducer from './comments'
import commentReducer from './comment'

const rootReducer = combineReducers({
  posts: postsReducer,
  comments: commentsReducer,
  post: postReducer,
  comment: commentReducer,
})

export default rootReducer
