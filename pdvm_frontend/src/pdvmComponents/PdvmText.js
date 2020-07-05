import styled from 'styled-components';

export const PdvmText = styled.p`
  ${({ theme }) => `
  text-transform: none ;
  background-color: ${theme.palette.primary.light} ;
  color: ${theme.palette.text.secondary}} ;
  box-shadow: 0 4px 6px rgba(50, 50, 93, 0.11), 0 1px 3px rgba(0, 0, 0, 0.08) ;
  padding: 0px 30px ;
  margin-left: 0.4em ;
  margin-top: 0.4em ;
  margin-botton: 0.4em ;
  fontFamily: "${theme.typography.button.fontFamily}}" ;
  fontSize: ${theme.typography.button.fontSize}} ;
  fontWeight: ${theme.typography.button.fontWeight}} ;
  letterSpacing: ${theme.typography.button.letterSpacing}} ;
  lineHeight: ${theme.typography.button.lineHeight}} ;
  `}
`;
