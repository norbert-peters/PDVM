import React from "react";
import { useForm } from "react-hook-form";
import { useDispatch } from 'react-redux'

import { putPost, postPost } from '../slices/post'

import { PdvmButton } from '../pdvmComponents/PdvmButton'
import  {PdvmTextField } from '../pdvmComponents/PdvmTextField'
//import { getThemeProps } from "@material-ui/styles";
//import { themes } from "../pdvmThemes/themes";
//import { themes } from "../pdvmThemes/themes";
//import Label from '@material-ui/core/FormLabel'
//import TextField from '@material-ui/core/TextField'

export default function PostEdit(props) {
  const dispatch = useDispatch()

  const { register, handleSubmit, errors } = useForm({
      defaultValues: {
        id: props.post.id,
        userId: props.post.userId,
        title: props.post.title,
        body: props.post.body,
      },
  })

  const createFlag = props.post.body === '' ? true : false

  const onSubmit = (data) => {
    const npres = {
      id: props.post.id,
      userId: props.post.userId,
      title: data.title,
      body: data.body,    
    }
    
    if (createFlag) {
      dispatch(postPost(npres))
    } else {
      dispatch(putPost(npres["id"], npres))
    }
    alert("Die Änderung wurde gespeichert");
  }

  return (
    <>
    <form onSubmit={handleSubmit(onSubmit)}>
      <PdvmTextField
        fullWidth
        size="small"
        aria-invalid={errors.title ? "true" : "false"}
        aria-describedby="nameError"
        id="outlined-required"
        name="title"
        label='Titel'
        variant='outlined'
        inputRef={register({ required: true })}
      />
      <span id="NameError" style={{ display: errors.title ? "block" : "none" }}>
        Das Feld Name ist erforderlich
      </span>
      <br />
      <PdvmTextField
          id="outlined-multiline"
          label="Artikel"
          multiline
          fullWidth
          variant="outlined"
          aria-invalid={errors.body ? "true" : "false"}
          aria-describedby="bodyError"
          name="body"
          inputRef={register({ required: true })}
        />
      <span id="bodyError" style={{ display: errors.body ? "block" : "none" }}>
        Das Feld Artikel ist erforderlich
      </span>
      <br />

      <PdvmButton pdvmstyle='text' display='attention' type="submit" >
        Daten speichern
      </PdvmButton>
    </form>
  </>  );
} 
