import React from 'react'
import { useQuery, queryCache, useMutation } from "react-query";

import axios from 'axios'

const API_URL = 'http://localhost:8000'

const getPost = async (key, id) => {
    const { data } = await axios.get(
    `${API_URL}/api/posts/${id}`
  )
  return data
}

const putPost = async (post) => {
  const id = post.id
  const { data } = await axios.put(
    `${API_URL}/api/posts/${id}`, post
  )
  return data
}

const postPost = async (post) => {
  const { data } = await axios.post(
    `${API_URL}/api/posts/`, post
  )
  return data
}

function GetPost(id) {
  return useQuery(['post', id ], getPost)
}

function PutPost(post) {
  return useMutation(
    post => putPost(post),
    {
      // bei Fehler
      onError: (err, variables, previousValue ) => {
        queryCache.setQueryData('posts', previousValue)
        alert('Fehler beim Speichern\n'+err)
        post.ret= "-1"
      },

      // wird so immer ausgeführt
      onSettled: () => {
        queryCache.invalidateQueries('posts')
        console.log('onSettled', queryCache)
      },

      // wenn es gespeichert wurde
      onSuccess: () => {
        alert('Daten geändert')
        post.ret = "0"
      },
    } 
  )
}

function PostPost(post) {
  return useMutation(
    post => postPost(post),
    {
      /*Aktualisieren Sie den Cache-Wert in Mutate optimistisch, 
      speichern Sie jedoch den alten Wert und geben Sie ihn zurück, 
      damit Sie im Fehlerfall darauf zugreifen können */      
      // bei Fehler
      onError: (err, variables, previousValue) => {
        queryCache.setQueryData('posts', previousValue)
        alert('Fehler beim Speichern\n'+err)
        post.ret= "-1"
      },

      // wird so immer ausgeführt
      onSettled: () => {
        queryCache.invalidateQueries('posts')
        console.log('onSettled', queryCache)
      },

      // wenn es gespeichert wurde
      onSuccess: () => {
        alert('Daten hinzugefügt')
        post.ret="0"
      },
    }
  )
}

function returnGetPost(id) {
  const { isLoading, data, isError, error } = GetPost(id)

if (isError) {
  return <div>{error.message}</div> // error state
}

if (isLoading) {
  return <div>Daten werden geladen...</div> // loading state
}
return data
}



export { GetPost, returnGetPost, PostPost, PutPost }