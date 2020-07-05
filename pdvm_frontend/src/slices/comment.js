import { createSlice } from '@reduxjs/toolkit'
import axios from 'axios'

export const initialState = {
  loading: false,
  creating: false,
  hasErrors: false,
  comment: [],
}

const commentSlice = createSlice({
  name: 'comment',
  initialState,
  reducers: {
    getComment: state => {
      state.loading = true
      state.creating = false
    },
    getCommentSuccess: (state, { payload }) => {
      state.comment = payload
      state.loading = false
      state.creating = false
      state.hasErrors = false
    },
    getCommentFailure: state => {
      state.loading = false
      state.creating = false
      state.hasErrors = true
    },
    getCommentCreate: state => {
      state.loading = false
      state.creating = true
      state.hasErrors = false
    },
  },
})

export const {
  getComment,
  getCommentSuccess,
  getCommentFailure,
  getCommentCreate,
} = commentSlice.actions

export const commentSelector = state => state.comment
export default commentSlice.reducer

export function fetchComment(id) {
  return async dispatch => {
    dispatch(getComment())

    try {
      const response = await axios.get(
        `http://localhost:8000/api/comments/${id}`
      )
      const data = await response.data
      dispatch(getCommentSuccess(data))
    } catch (error) {
      dispatch(getCommentCreate())
    }
  }
}

export function putComment(id, comment) {
  return async dispatch => {
    dispatch(getComment())

    try {
      const response = await axios.put(
        `http://localhost:8000/api/comments/${id}`, comment
      )
      const data = await response.data
      dispatch(getCommentSuccess(data))
    } catch (error) {
      dispatch(getCommentFailure())
    }
  }
}

export function postComment(comment) {
  return async dispatch => {
    dispatch(getComment())

    try {
      const response = await axios.post(
        `http://localhost:8000/api/comments/`, comment
      )
      const data = await response.data
      console.log('nach Aufruf POST')
      console.log(data)
      dispatch(getCommentSuccess(data))
    } catch (error) {
      dispatch(getCommentFailure())
    }
  }
}
