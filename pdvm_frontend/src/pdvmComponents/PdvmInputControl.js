import React, { useState, useEffect, useRef } from 'react'
import styled from "styled-components";
 
import Textarea from 'react-expanding-textarea'
import { theme } from '../theme';


const InputContainer = styled.div`
  display: flex;
  flex-direction: column;
  position: relative;
  background-color: ${props => (
    props.focused ? `${theme.back.inputHover}` 
    : `${theme.back.input}`)};
  border: 0.2rem solid ${props => (
    props.error ? `${theme.error.main}` 
    : `${theme.back.input}`)};
  border-radius: 0.25rem;
  margin-top: 2px;
 
  & > textarea {
    background-color: ${props => (
      props.isShown ? `${theme.back.inputHover}`
        : props.focused ? `${theme.back.inputActiv}` 
      : `${theme.back.input}`)};
    color: ${props => (
      props.focused ? `${theme.front.text}` 
      : `${theme.front.text}`)};
    }

  & > label {    
    background-color: ${props => (
      props.focused ? `${theme.back.inputActiv}` 
      : `${theme.back.input}`)};
    color: ${props => (
      props.error ? `${theme.error.main}` 
      : props.isActiv ? `${theme.front.label}` 
        : `${theme.front.labelLight}`)};
    position: absolute;
    top: 15px;
    left: 15px;
    font-weight:${theme.typography.fontWeightBold};

    ${props => 
      props.isShown &&
      `background-color: ${theme.back.inputHover};
      `}


    ${props =>
      props.isActiv &&
      `
      font-size: ${theme.typography.fontSizeSmall};
      outline: none;
      transform: translateY(-15px) translateX(-15px);
      padding: 1px 1px;
    `}
  }
`;

const MyTextarea = (props) => {
  const textareaRef = useRef(props)

  useEffect(() => {
    textareaRef.current.focus()
  }, [])

  return (
    <>
      <Textarea
        ref={textareaRef}
        {...props}
      />
    </>
  )
}

const MyTextareaS = styled(MyTextarea)`
${({ theme }) => `
  border: 1em ;
  outline: none;
  padding: 20px 0 0 15px;
  background-color: ${theme.back.input};
  color: ${theme.front.input};
  font-family: ${theme.typography.fontFamily};
  font-size: ${theme.typography.fontSize};
  resize: none;
  `}
`;
const MyTextareaT = styled(MyTextarea)`
  border: 0rem ;
  outline: none;
  padding: 20px 0 0 15px;
  font-family: ${theme.typography.fontFamily};
  font-size: ${theme.typography.fontSize};
  resize: none;
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
const PdvmInputControl = ({
  id,
  pdvmType,
  multiline,
  value,
  type,
  label,
  onChange,
  onFocus,
  onBlur,
  setRef,
  num,
  ref,
  ...props
}) => {
  const [focused, setFocused] = useState(false);
  const [error, setError] = useState(null);
  const [isShown, setIsShown] = useState(false);
  
  const handleOnFocus = () => {
    setFocused(true);
    onFocus();
  };

  const handleOnBlur = () => {
    setFocused(false);
    onBlur();
  };

  const validateValue = val => {
    if (type === "email") {
      // VERY simple email validation
      if (val.indexOf("@") === -1) {
        setError("Email ist nicht korrekt");
      } else {
        setError(null);
      }
    }

    // ... any other validation you could think of
    // ... maybe even pass in an additional validation function as a prop?
  };

  const handleOnChange = val => {
    validateValue(val);
    onChange(val);
  };

  const renderLabel = () => {
    if (label) {
      // if we have an error
      if (error) {
        return <label>{error}</label>;
      }

      return <label>{label}</label>;
    }
    return null;
  };

  const isFocused = focused || String(value).length || type === "date";

  function pdvmControl(props) {
    switch (pdvmType) {
      case 'textonly':
        return <MyTextareaS
          value={value}   
          type={type} 
          rows={1}
          onChange={e => handleOnChange(e.target.value)} 
          onFocus={handleOnFocus} 
          onBlur={handleOnBlur} 
          num={num}
          setref={ref}
          {...props}
        />
        case 'textarea':
          return <MyTextareaS
          value={value}   
          type={type} 
          onChange={e => handleOnChange(e.target.value)} 
          onFocus={handleOnFocus} 
          onBlur={handleOnBlur} 
          num={num}
          setref={ref}
          {...props}
        />      
        case 'readonly':
          return <MyTextareaT
          defaultValue={value}   
          type={type} 
          num={num}
          {...props}
        />      
        default:
         return console.log('pdvmType', pdvmType, 'nicht bekannt')
      }
  }

  return (
    <InputContainer 
      focused={focused} 
      isActiv={isFocused} 
      error={error}
      onMouseEnter={() => setIsShown(true)}
      onMouseLeave={() => setIsShown(false)}
      isShown={isShown}
    >
      {renderLabel()}
      {pdvmControl(props)}
    </InputContainer>
  );
};

PdvmInputControl.defaultProps = {
  type: "text",
  label: "",
  onChange: text => {
    console.error(`Vermisse die onChange Eigenschaft: ${text}`);
  },
  onFocus: () => {},
  onBlur: () => {},
  setRef: () => {},
};

export default PdvmInputControl;
