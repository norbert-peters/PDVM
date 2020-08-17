import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { fetchPost, postSelector } from '../slices/post'
import { fetchComment, commentSelector } from '../slices/comment'

import { Post } from '../components/Post'
import  CommentEdit  from '../components/CommentEdit'

import { PdvmSection } from '../pdvmComponents/PdvmSection'


const EditCommentPage = ({ match }) => {
  const dispatch = useDispatch()
  const { 
    post, 
    loading: postLoading, 
    hasErrors: postHasErrors 
  } = useSelector(postSelector)
  var {
    comment,
    creating: commentCreating,
    loading: commentLoading,
    hasErrors: commentHasErrors,
  } = useSelector(commentSelector)

  useEffect(() => {
    var { id, postId } = match.params
    console.log(id)
    console.log(postId)
    
    dispatch(fetchComment(id))

    dispatch(fetchPost(postId))

  }, [dispatch, match])

  const renderPost = () => {
    if (postLoading) return <p>Loading post...</p>
    if (postHasErrors) return <p>Unable to display post.</p>
    return <Post post={post} />
  }

  const renderComment = () => {
    if (commentLoading) return <p>Loading comment...</p>
    if (commentHasErrors) return <p>Unable to display comment.</p>
    if (commentCreating) {
      comment = {
        id: match.params.id,
        postId: match.params.postId,
        name: '',
        email: '',
        body: '',
      }
    }
    return <CommentEdit comment={comment} />
  }

  return (
    <PdvmSection>
    {renderPost()}
      <h2>Kommentar modifizieren</h2>
      {renderComment()}
    </PdvmSection>
  )
}

export default EditCommentPage
