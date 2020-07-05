import React, { useEffect } from 'react'
import { Link as RouterLink } from 'react-router-dom'

import { useDispatch, useSelector } from 'react-redux'

import { fetchPosts, getPostsByURL, postsSelector } from '../slices/posts'

import { Post } from '../components/Post'

import * as uuid from 'uuid'
import PdvmPagination from '../pdvmComponents/PdvmPagination'
//import {PdvmButton} from '../pdvmComponents/PdvmButton'
import {PdvmSection} from '../pdvmComponents/PdvmSection'
import {PdvmFlexBox} from '../pdvmComponents/PdvmFlexBox'
import AddIcon from '@material-ui/icons/Add';
import Fab from '@material-ui/core/Fab';
import Tooltip from '@material-ui/core/Tooltip';
import { Box } from '@material-ui/core'
//import Paper from '@material-ui/core/Paper';




const PostsPage = () => {
  const art = 'Artikel' 
  const dispatch = useDispatch()
  const { 
    posts, 
    loading, 
    hasErrors,
    nextPageURL,
    prevPageURL,
    numPages, 
    count,
    pageNumber, 
  } = useSelector(postsSelector)

  useEffect(() => {

    dispatch(fetchPosts())
  }, [dispatch])

  function prevPage(){
    dispatch(getPostsByURL(prevPageURL))
  }
  
  function nextPage(){
    dispatch(getPostsByURL(nextPageURL))
  }
  
  const renderPosts = () => {
    if (loading) return <p>Loading posts...</p>
    if (hasErrors) return <p>Unable to display posts.</p>
    return posts.map(post => <Post key={post.id} post={post} excerpt />)
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
      <PdvmFlexBox>
    <h1>Artikel</h1>
    <Box marginLeft='5em' padding='1em'>
      <Tooltip 
        title="Artikel hinzufügen" 
        aria-label="add" 
        component={RouterLink} 
        to={`/post/postedit/${uuid.v4()}`}
      >
        <Fab color="secondary" >
          <AddIcon />
        </Fab>
      </Tooltip>
      </Box>
      </PdvmFlexBox>
      {renderPdvmPagination()}
      {renderPosts()}
      {renderPdvmPagination()}
    </PdvmSection>
   
  )
}

export default PostsPage
