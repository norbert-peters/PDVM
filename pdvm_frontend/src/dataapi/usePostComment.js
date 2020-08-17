import { useQuery } from "react-query";
import axios from 'axios'

const API_URL = 'http://localhost:8000'

const getPostComments = async (key, id, nlink) => {
  const link = nlink ? nlink : `/api/postcomments/${id}/?page=1`
    const { data } = await axios.get(
      `${API_URL}${link}`
      )
  return data
}

export default function usePostComment(postId, nlink) {
 return useQuery(['comments', postId, nlink ], getPostComments)
}
