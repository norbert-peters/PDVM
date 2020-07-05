import { createSlice } from '@reduxjs/toolkit'
import axios from 'axios'

const API_URL = 'http://localhost:8000'

export const initialState = {
  nextPageURL: '',
  prevPageURL: '',
  numPages: 0,
  count: 0,
  loading: false,
  hasErrors: false,
  comments: [],
}

const commentsSlice = createSlice({
  name: 'comments',
  initialState,
  reducers: {
    getComments: state => {
      state.loading = true
    },
    getCommentsSuccess: (state, { payload }) => {
      console.log('getSuccess ', payload)
      state.comments = payload.data
      state.nextPageURL = payload.nextlink
      state.prevPageURL = payload.prevlink
      state.numPages = payload.numpages
      state.count = payload.count
      state.pageNumber = payload.pagenumber
      state.loading = false
      state.hasErrors = false
    },

    getCommentsFailure: state => {
      state.loading = false
      state.hasErrors = true
    },
  },
})

export const {
  getComments,
  getCommentsSuccess,
  getCommentsFailure,
} = commentsSlice.actions
export const commentsSelector = state => state.comments
export default commentsSlice.reducer

export function fetchComments(postId) {
  return async dispatch => {
    dispatch(getComments())

    try {
      const response = await axios.get(
        `${API_URL}/api/postcomments/${postId}`
      )
      console.log(response)
      const data = await response.data

      dispatch(getCommentsSuccess(data))
    } catch (error) {
      dispatch(getCommentsFailure())
    }
  }
}

export function getCommentsByURL(link) {
  return async dispatch => {
    dispatch(getComments())
    try {
      const response = await axios.get(`${API_URL}${link}`)
      const data = await response.data
      dispatch(getCommentsSuccess(data))
    } catch (error) {
      dispatch(getCommentsFailure())
    }
  }
}
