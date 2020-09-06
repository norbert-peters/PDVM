import React from 'react'
import { useQuery, queryCache, useMutation } from "react-query";

import axios from 'axios'

const API_URL = 'http://localhost:8000'

const getComment = async (key, id) => {
    const { data } = await axios.get(
    `${API_URL}/api/comments/${id}`
  )
  return data
}

const putComment = async (comment) => {
  const id = comment.id
  const { data } = await axios.put(
    `${API_URL}/api/comments/${id}`, comment
  )
  return data
}


const postComment = async (comment) => {
  const { data } = await axios.post(
    `${API_URL}/api/comments/`, comment
  )
  return data
}

function GetComment(id) {
  return useQuery(['comment', id ], getComment)
}

function PutComment(comment) {
  return useMutation(
    comment => putComment(comment),
    {
      // bei Fehler
      onError: (err, variables, previousValue ) => {
        queryCache.setQueryData('comments', previousValue)
        alert('Fehler beim Speichern\n'+err)
        comment.ret= "-1"
      },

      // wird so immer ausgeführt
      onSettled: () => {
        queryCache.invalidateQueries('comments')
        console.log('onSettled', queryCache)
      },

      // wenn es gespeichert wurde
      onSuccess: () => {
        alert('Daten geändert')
        comment.ret = "0"
      },
    } 
  )
}

function PostComment(comment) {
  return useMutation(
    comment => postComment(comment),
    {
      /*Aktualisieren Sie den Cache-Wert in Mutate optimistisch, 
      speichern Sie jedoch den alten Wert und geben Sie ihn zurück, 
      damit Sie im Fehlerfall darauf zugreifen können */      
      // bei Fehler
      onError: (err, variables, previousValue, Response) => {
        queryCache.setQueryData('comments', previousValue)
        alert('Fehler beim Hinzufügen\n'+err)
        comment.ret= "-1"

      },

      // wird so immer ausgeführt
      onSettled: () => {
        queryCache.invalidateQueries('comments')
        console.log('onSettled', queryCache)
      },

      // wenn es gespeichert wurde
      onSuccess: () => {
        alert('Daten hinzugefügt')
        comment.ret="0"
      },
    }
  )
}

function returnGetComment(id) {
  const { isLoading, data, isError, error } = GetComment(id)

  if (isError) {
    return <div>{error.message}</div> // error state
  }

  if (isLoading) {
    return <div>Daten werden geladen...</div> // loading state
  }
  return data
}

export { returnGetComment, GetComment, PostComment, PutComment }
