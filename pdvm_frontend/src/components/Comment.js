import React from 'react'
import { PdvmPaper } from '../pdvmComponents/PdvmPaper'
import EditTwoTone from '@material-ui/icons/Edit'
import PdvmInputControl from '../pdvmComponents/PdvmInputControl';
import { PdvmHeader } from '../pdvmComponents/PdvmHeader'

function myButton(comment) {  
  return [
  {
    "id": 0,
    "ttitle" : "Kommentar ändern", 
    "togo" : `/post/postsedit/${comment.id}/${comment.postId}/mod`, 
    "nicon" : <EditTwoTone /> 
  },
]
}

export const Comment = ({ comment }) => (
  <PdvmPaper >
    <PdvmHeader
      phType='h1'
      phTitle={comment.name}
      phButton={myButton(comment)}
      phPost={comment}
      phExcerpt='true'
    />
    <PdvmHeader
      phType='h3'
      phTitle={comment.email}
      phPost={comment}
    />
    <PdvmInputControl
      pdvmType="textonly"
      value={comment.body}
      readOnly
    />
  </PdvmPaper>
)

