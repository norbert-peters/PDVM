import React, { useEffect } from 'react'
import { Link as RouterLink} from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'

import { fetchPost, postSelector } from '../slices/post'
import { fetchComments, getCommentsByURL, commentsSelector } from '../slices/comments'

import { Post } from '../components/Post'
import { Comment } from '../components/Comment'
//import { PdvmButton } from '../pdvmComponents/PdvmButton'
import { PdvmSection } from '../pdvmComponents/PdvmSection'
import PdvmPagination from '../pdvmComponents/PdvmPagination'

import {PdvmFlexBox} from '../pdvmComponents/PdvmFlexBox'
import AddIcon from '@material-ui/icons/Add';
import Fab from '@material-ui/core/Fab';
import Tooltip from '@material-ui/core/Tooltip';
import { Box } from '@material-ui/core'

import * as uuid from 'uuid'

const SinglePostPage = ({ match }) => {
  const dispatch = useDispatch()
  const { 
    post, 
    loading: postLoading, 
    hasErrors: postHasErrors 
  } = useSelector(postSelector)
  const art = 'Kommentare' 
  const { 
    comments, 
    loading: commentsLoading,
    hasErrors: commentsHasErrors,
    nextPageURL,
    prevPageURL,
    numPages, 
    count,
    pageNumber, 
  } = useSelector(commentsSelector)

  useEffect(() => {
    const { id } = match.params

    dispatch(fetchComments(id))
    dispatch(fetchPost(id))
  }, [dispatch, match])

  const renderPost = () => {
    if (postLoading) return <p>Loading post...</p>
    if (postHasErrors) return <p>Unable to display post.</p>
    return <Post post={post} />
  }

  function prevPage(){
    dispatch(getCommentsByURL(prevPageURL))
  }
  
  function nextPage(){
    dispatch(getCommentsByURL(nextPageURL))
  }

  const renderComments = () => {
    if (commentsLoading) return <p>Loading comments...</p>
    if (commentsHasErrors) return <p>Unable to display comments.</p>

    return comments.map(comment => <Comment key={comment.id} comment={comment} excerpt />)
  }

  const renderPdvmPagination = () => {
    return <PdvmPagination 
      nextPage={nextPage}
      prevPage={prevPage}
      pageNumber={pageNumber}
      numPages={numPages}
      count={count}
      art={art}
    />
}

  return (
    <PdvmSection>
      <br />
      {renderPost()}
      <PdvmFlexBox>
        <h1>Kommentare</h1>
        <Box marginLeft='5em' padding='1em'>
          <Tooltip 
            title="Kommentar hinzufügen" 
            aria-label="add" 
            component={RouterLink} 
            to={`/post/postsedit/${uuid.v4()}/${post.id}`}
          >
            <Fab color="secondary" >
              <AddIcon />
            </Fab>
          </Tooltip>
        </Box>
      </PdvmFlexBox>
      {renderPdvmPagination()}
      {renderComments()}
      {renderPdvmPagination()}
    </PdvmSection>
  )
}

export default SinglePostPage
