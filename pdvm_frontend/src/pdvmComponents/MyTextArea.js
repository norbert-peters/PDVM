import React, { useCallback, useEffect, useRef } from 'react'
import Textarea from 'react-expanding-textarea'

export const MyTextarea = () => {
  const textareaRef = useRef(null)

  const handleChange = useCallback(e => {
    console.log('Changed value to: ', e.target.value)
  }, [])

  useEffect(() => {
    textareaRef.current.focus()
  }, [])

  return (
    <>
      <Textarea
        className="textarea"
        defaultValue="Lorem ipsum dolor sit amet, ..."
        id="my-textarea"
        maxLength="3000"
        name="pet[notes]"
        onChange={handleChange}
        placeholder="Enter additional notes..."
        ref={textareaRef}
      />
    </>
  )
}