import styled from 'styled-components';
import {
  darken,
} from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';

export const PdvmButton = styled(Button)`
  ${({ theme }) => `
  text-transform: none ;
  background-color: ${theme.palette.primary.light} ;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08) ;
  padding: 4px 10px ;
  margin-left: 0.4em;
  margin-top: 0.2em ;
  margin-bottem: 0.2em ;
  fontFamily: ${theme.typography.button.fontFamily}} ;
  fontSize: ${theme.typography.button.fontSize}} ;
  fontWeight: ${theme.typography.button.fontWeight}} ;
  letterSpacing: ${theme.typography.button.letterSpacing}};
  lineHeight: ${theme.typography.button.lineHeight}} ;
  &:hover {
    background-color: ${darken(theme.palette.primary.main, 0.2)} ;
  }
  ${theme.breakpoints.up('sm')} {
    font-size: 14px ;
    font-weight: 700 ;
    padding: 7px 14px ;
  }
  `}
`;
