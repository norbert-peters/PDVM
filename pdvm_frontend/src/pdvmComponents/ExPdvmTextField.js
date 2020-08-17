import styled from 'styled-components';
import TextField from '@material-ui/core/TextField';
//import {darken} from '@material-ui/core/styles';

export const ExPdvmTextField = styled(TextField)`
${({ theme }) => `
  label.focused {
    color: green; 
  }
  input {
      color :  green, 
      fontWeight: "bold",
  }, 

  label {
    color: ${theme.primaryLight};
  }
  margin-bottom: 0.4em;
  .MuiOutlinedInput-root {
    color: 'main';
    fieldset {
      border-color: blue; 
    }
    &:hover fieldset {
      border-color: pink; 
    }
    &.Mui-focused fieldset {
      border-color: green; 
    }
  }
  `}
`;
