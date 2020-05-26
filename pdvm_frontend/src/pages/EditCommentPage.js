import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { fetchPost, postSelector } from '../slices/post'
import { fetchComment, commentSelector } from '../slices/comment'

import { Post } from '../components/Post'
import  CommentEdit  from '../components/CommentEdit'

const EditCommentPage = ({ match }) => {
  const dispatch = useDispatch()
  const { 
    post, 
    loading: postLoading, 
    hasErrors: postHasErrors 
  } = useSelector(postSelector)
  const {
    comment,
    loading: commentLoading,
    hasErrors: commentHasErrors,
  } = useSelector(commentSelector)

  useEffect(() => {
    const { id, postId } = match.params
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
    return <CommentEdit comment={comment} />
  }

  return (
    <section>
      {renderPost()}
      <h2>Kommentar modifizieren</h2>
      {renderComment()}
    </section>
  )
}

export default EditCommentPage
