import styled from 'styled-components';
import {
  darken,
  lighten,
} from '@material-ui/core/styles';

export const PdvmButton = styled.button`
  ${({ theme }) => `
  text-transform: none ;
  background-color: ${theme.back.button} ;
  box-shadow: 0 4px 6px ${theme.shadow.main}, 0 1px 3px ${theme.shadow.dark};
  padding: 4px 10px ;
  margin-left: 0.4em;
  margin-top: 0.2em ;
  margin-bottem: 0.2em ;
  font-family: ${theme.typography.fontFamily}} ;
  font-size: ${theme.typography.fontSize}} ;
  font-weight: ${theme.typography.fontWeightBold}} ;
  letter-spacing: ${theme.typography.letterSpacing}};
  line-height: ${theme.typography.lineHeight}} ;
  &:hover {
    background-color: ${darken(theme.back.buttonHover, 0.3)} ;
    color: ${lighten(theme.front.buttonHover, 0.8)}
    font-weight: ${theme.typography.fontWeightMedium}} ;
  }
  `}
`;
