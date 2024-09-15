import styled from 'styled-components';

export const PdvmText = styled.p`
  ${({ theme }) => `
  text-transform: none ;
  background-color: ${theme.back.default} ;
  color: ${theme.front.text}} ;
  box-shadow: 3px 3px 1px ${theme.shadow.main};
  padding: 0px 30px ;
  margin-left: 0.4em ;
  margin-top: 1em ;
  margin-botton: 0.4em ;
  font-family: ${theme.typography.fontFamily} ;
  font-size: ${theme.typography.fontSize}} ;
  font-weight: ${theme.typography.fontWeight} ;
  `}
`;
