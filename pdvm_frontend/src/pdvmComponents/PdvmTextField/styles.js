import React from 'react'
import styled from 'styled-components'

const InputContainer = styled.div`
  display: flex;
  flex-direction: column;
  margin: 15px 0;
  position: relative;

  & > input {
    border: 1px solid #eee;
    border-radius: 0.25rem;
    background-color: transparent;
    outline: none;
    padding: 12px 3px 12px 15px;
    font-size: 16px;
    transition: all 0.2s ease;
    z-index: 500;
  }
  & > label {
    color: #757575;
    position: absolute;
    top: 15px;
    left: 15px;
    transition: all 0.2s ease;
    z-index: 500;
  }
`

/**
 * A Plaid-inspired custom input component
 * 
 * @param {string} value - the value of the controlled input
 * @param {string} type - the type of input we'll deal with
 * @param {string} label - the label used to designate info on how to fill out the input
 * @param {function} onChange - function called when the input value changes
 * @param {function} onFocus - function called when the input is focused
 * @param {function} onBlur - function called when the input loses focus
 * @param {function} setRef - function used to add this input as a ref for a parent component
 */
const PdvmTextField = ({
  value,
  type,
  label,
  onChange,
  onFocus,
  onBlur,
  setRef,
  ...props
}) => {
  const renderLabel = () => label && <label>{ label }</label>

  return (
    <InputContainer>
      { renderLabel() }
      <input 
        value={value}
        type={type}
        onChange={e => onChange(e.target.value)}
        onFocus={onFocus}
        onBlur={onBlur}
        {...props}
      />
    </InputContainer>
  )
}

PdvmTextField.defaultProps = {
  type: "text",
  label: "",
  onChange: (text) => { console.error(`Missing onChange prop: ${text}`) },
  onFocus: () => {},
  onBlur: () => {},
  setRef: () => {},
}

export default PdvmTextField
