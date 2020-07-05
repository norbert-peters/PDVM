//import React from 'react'
import Box from '@material-ui/core/Box'
import styled from 'styled-components'

export const PdvmFlexBox = styled(Box)`
${({ theme }) => `
  display: flex ;
  color: ${theme.palette.text.primary}} ;
  background-color: ${theme.palette.primary.light} ;
  padding: 0.3em 0.7em ;
​​  margin-top: 0.1em ;
  margin-left: 0.2em ;
  hight: 0.5 em;
  `}
`;
