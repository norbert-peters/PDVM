import styled from 'styled-components';
import {
  darken,
} from '@material-ui/core/styles';
//import Button from '@material-ui/core/Button';

export const PdvmButton = styled.button`
  ${({ theme }) => `
  text-transform: none ;
  background-color: ${theme.primaryDark} ;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08) ;
  padding: 4px 10px ;
  margin-left: 0.4em;
  margin-top: 0.2em ;
  margin-bottem: 0.2em ;
  fontFamily: ${theme.typography.fontFamily}} ;
  fontSize: ${theme.typography.fontSize}} ;
  fontWeight: ${theme.typography.fontWeight}} ;
  letterSpacing: ${theme.typography.letterSpacing}};
  lineHeight: ${theme.typography.lineHeight}} ;
  &:hover {
    background-color: ${darken(theme.primaryDark, 0.2)} ;
  }
  `}
`;
