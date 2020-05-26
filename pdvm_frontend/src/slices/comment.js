import { createSlice } from '@reduxjs/toolkit'
import axios from 'axios'

export const initialState = {
  loading: false,
  hasErrors: false,
  comment: [],
}

const commentSlice = createSlice({
  name: 'comment',
  initialState,
  reducers: {
    getComment: state => {
      state.loading = true
    },
    getCommentSuccess: (state, { payload }) => {
      state.comment = payload
      state.loading = false
      state.hasErrors = false
    },
    getCommentFailure: state => {
      state.loading = false
      state.hasErrors = true
    },
    setComment: (state, { comment }) => {
      state.comment = comment
      state.loading = true
      state.hasErrors = false
    },
  },
})

export const {
  getComment,
  getCommentSuccess,
  getCommentFailure,
  setComment,
} = commentSlice.actions
export const commentSelector = state => state.comment
export default commentSlice.reducer

export function putComment(comment, id) {
  console.log('angekommen')
  console.log(comment)
  return async dispatch => {
    dispatch(setComment(comment))

    try {
      console.log('vor patch:', comment )
      await axios.put(
        `http://localhost:8000/api/comments/${id}`, comment
      )
//      console.log('Returned data:', response);
//      const data = await response.data
//      console.log(data)
//      dispatch(getCommentSuccess(data))
    } catch (e) {
      console.log("Fehler")
      dispatch(getCommentFailure())
      console.log(`Axios request failed: ${e}`);
    }
  }
}


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
      dispatch(getCommentFailure())
    }
  }
}
