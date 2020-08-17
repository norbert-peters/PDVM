import React, { useState } from 'react'
import { Link as RouterLink} from 'react-router-dom'
import { GetPost } from '../dataapi/Post'

import { Post } from '../components/Post'
import { Comment } from '../components/Comment'
import { PdvmSection } from '../pdvmComponents/PdvmSection'
import PdvmPagination from '../pdvmComponents/PdvmPagination'

import {PdvmFlexBox} from '../pdvmComponents/PdvmFlexBox'
import AddIcon from '@material-ui/icons/Add';
import Fab from '@material-ui/core/Fab';
import Tooltip from '@material-ui/core/Tooltip';
import { Box } from '@material-ui/core'
import { Row, Col } from '../pdvmComponents/PdvmRaster';


import * as uuid from 'uuid'
import usePostComment from '../dataapi/usePostComment'

function SinglePostPage(props) {
  const [nlink, setNlink] = useState('')
  const startPostid = props.match.params.id
  const [postid] = useState(startPostid)
  const post = GetPost(postid)
  
const { isLoading, data, isError, error } = usePostComment(postid, nlink)

if (isError) {
  return <div>{error.message}</div> // error state
}

if (isLoading) {
  return <div>loading...</div> // loading state
}
  
  const art_s = 'Kommentar'
  const art_p = 'Kommentare'
  const pcomments = data.data 
  const pagenumber = data.pagenumber
  const numpages = data.numpages
  const count = data.count
  const pdvm = 'new'

  const renderPost = (
    <Post post={post} />
  )

  const renderComments = (
    pcomments.map(comment => <Comment key={comment.id} comment={comment} excerpt />)
  ) 

  function prevPage(){
    setNlink(data.prevlink)
  }
  
  function nextPage(){
    setNlink(data.nextlink)
  }

  const renderPdvmPagination = () => {
    return <PdvmPagination 
      nextPage={nextPage}
      prevPage={prevPage}
      pagenumber={pagenumber}
      numpages={numpages}
      count={count}
      art={art_p}
    />
  }

  return (
    <div>
      {renderPost}
      <PdvmFlexBox>
        <Row>
        <Col size={1}>
        <h1>{art_p}</h1>
        </Col>
        <Col size={2}></Col>
        <Col size={1}>
        <Box marginLeft='5em' padding='1em'>
          <Tooltip 
            title={`${art_s} hinzufügen`} 
            aria-label="add" 
            component={RouterLink} 
            to={`/post/postsedit/${uuid.v4()}/${pdvm}`}
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
      {renderComments}
      {renderPdvmPagination()}
    </PdvmSection>
    </div>
  )
}

export default SinglePostPage
