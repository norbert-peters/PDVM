import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'

import { fetchPost, postSelector } from '../slices/post'

import  PostEdit  from '../components/PostEdit'
import { PdvmSection } from '../pdvmComponents/PdvmSection'


const EditPostPage = ({ match }) => {
  const dispatch = useDispatch()
  var { 
    post, 
    creating: postCreating,
    loading: postLoading, 
    hasErrors: postHasErrors 
  } = useSelector(postSelector)

  useEffect(() => {
    var { id } = match.params
    console.log(id)
    
    dispatch(fetchPost(id))

}, [dispatch, match])

  const renderPost = () => {
    if (postLoading) return <p>Loading post...</p>
    if (postHasErrors) return <p>Unable to display post.</p>
    if (postCreating) {
      post = {
        id: match.params.id,
        userId: '99',
        title: '',
        body: '',
      }
    }
    return <PostEdit post={post} />
  }

  return (
    <PdvmSection>
        <br />
        <h1>Artikel modifizieren</h1>
        {renderPost()}
    </PdvmSection>
  )
}

export default EditPostPage
