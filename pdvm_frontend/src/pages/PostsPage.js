import React, {useState} from 'react'
import { Link as RouterLink } from 'react-router-dom'

import { Post } from '../components/Post'
import  usePosts  from '../dataapi/usePosts'

import * as uuid from 'uuid'
import PdvmPagination from '../pdvmComponents/PdvmPagination'
import {PdvmSection} from '../pdvmComponents/PdvmSection'
import {PdvmFlexBox} from '../pdvmComponents/PdvmFlexBox'
import AddIcon from '@material-ui/icons/Add';
import Fab from '@material-ui/core/Fab';
import Tooltip from '@material-ui/core/Tooltip';
import { Box } from '@material-ui/core';

import { Row, Col } from '../pdvmComponents/PdvmRaster';

function PostsPage({post, excerpt} ) {
    const [nlink, setNlink] = useState('')
    const { isLoading, isError, data, error } = usePosts(nlink)
  
    if (isError) {
      return <div>{error.message}</div> // error state
    }
  
    if (isLoading) {
        return <div>loading...</div> // loading state
    }

  const art = 'Artikel'
  const posts = data.data
  const pagenumber = data.pagenumber
  const numpages = data.numpages
  const count = data.count

  const renderPosts = (
    posts.map(post => <Post key={post.id} post={post} excerpt />)
  )

  const renderPdvmPagination = () => {
    return <PdvmPagination 
      nextPage={nextPage}
      prevPage={prevPage}
      pagenumber={pagenumber}
      numpages={numpages}
      count={count}
      art={art}
    />
}

  function prevPage(){
    setNlink(data.prevlink)
  }
  
  function nextPage(){
    setNlink(data.nextlink)
  }

  return (
    <div>
      <PdvmFlexBox>
        <Row>
          <Col size={1}>
            <h1>{art}</h1>
          </Col>
          <Col size={2}></Col>
          <Col size={1}>
            <Box marginLeft='5em' padding='1em'>
              <Tooltip 
                title={art + " hinzufügen"} 
                aria-label="add" 
                component={RouterLink} 
                to={`/post/postedit/${uuid.v4()}/new`}
              >
                <Fab color="secondary" >
                  <AddIcon />
                </Fab>
              </Tooltip>
            </Box>
          </Col>
        </Row>
      </PdvmFlexBox>
      <PdvmSection>
        {renderPdvmPagination()}
        {renderPosts}
        {renderPdvmPagination()}
      </PdvmSection>
    </div>  
  )
}

export default PostsPage
