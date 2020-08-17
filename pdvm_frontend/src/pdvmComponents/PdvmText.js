import styled from 'styled-components';

export const PdvmText = styled.p`
  ${({ theme }) => `
  text-transform: none ;
  background-color: ${theme.primaryLight} ;
  color: ${theme.primaryDark}} ;
  box-shadow: 3px 3px 1px #888888;
  padding: 0px 30px ;
  margin-left: 0.4em ;
  margin-top: 1em ;
  margin-botton: 0.4em ;
  fontFamily: "${theme.typography.fontFamily}}" ;
  fontSize: ${theme.typography.fontSize}} ;
  fontWeight: ${theme.typography.fontWeight}} ;
  letterSpacing: ${theme.typography.letterSpacing}} ;
  lineHeight: ${theme.typography.lineHeight}} ;
  `}
`;
