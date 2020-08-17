import React from "react";
import { useForm } from "react-hook-form";
import { useDispatch } from 'react-redux'

import { putComment, postComment } from '../slices/comment'
 
import { PdvmButton } from '../pdvmComponents/PdvmButton'
import  {ExPdvmTextField}  from '../pdvmComponents/ExPdvmTextField'
import { PdvmInput } from '../pdvmComponents/PdvmInput'
//import { StyledPdvmTextField } from '../pdvmComponents/PdvmTextField/styles';

//import { red } from "@material-ui/core/colors";



export default function CommentEdit(props) {
  console.log(props)
  console.log(props.comment.name)
  const dispatch = useDispatch()

  const { register, handleSubmit, errors } = useForm({
      defaultValues: {
        id: props.comment.id,
        postId: props.comment.postId,
        name: props.comment.name,
        email: props.comment.email,
        body: props.comment.body,
      },
  })

  const createFlag = props.comment.body === '' ? true : false

  const onSubmit = (data) => {
    const npres = {
      id: props.comment.id,
      postId: props.comment.postId,
      name: data.name,
      email: data.email,
      body: data.body,    
    }
    
    if (createFlag) {
      dispatch(postComment(npres))
    } else {
      dispatch(putComment(npres["id"], npres))
    }
    alert("Die Änderung wurde gespeichert");
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
    <PdvmInput
      value={props.comment.name}
      type="data"
      name="name"
      label="Name"
      setRef={register({ required: true })}
    />
      <ExPdvmTextField
        fullWidth
        size="small"
        aria-invalid={errors.email ? "true" : "false"}
        aria-describedby="mailError"
        variant="outlined"
        name="email"
        label="Email-Adresse"
        inputRef={register({ required: true })}
      />
      <span id="mailError" style={{ display: errors.email ? "block" : "none" }}>
        Das Feld Mail ist erforderlich
      </span>
      <br />
      <ExPdvmTextField
          id="outlined-multiline-static"
          label='Kommentar'
          multiline
          fullWidth
          variant="outlined"
          aria-invalid={errors.body ? "true" : "false"}
          aria-describedby="bodyError"
          name="body"
          inputRef={register({ required: true })}
      />
      <span id="bodyError" style={{ display: errors.body ? "block" : "none" }}>
        Das Feld Kommentar ist erforderlich
      </span>
      <br />

      <PdvmButton display='attention' type="submit" >
        Daten speichern
      </PdvmButton>
    </form>
  );
} 
