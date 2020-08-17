import styled from 'styled-components';
import { device, maxSize } from './PdvmDevice';

export const PdvmPage = styled.div`
  margin: auto;
  font-family: "sans-serif";
  text-align: center;
  background: ${({ theme }) => theme.primaryDark};
  color: ${({ theme }) => theme.primaryLight};

  @media ${device.mobileS} { 
    ${maxSize.mobileS};
  }

  @media ${device.mobileM} { 
    ${maxSize.mobileM};
  }

  @media ${device.mobileL} { 
    ${maxSize.mobileL};
  }

  @media ${device.tablet} { 
    ${maxSize.tablet};
  }

  @media ${device.laptop} { 
    ${maxSize.laptop};
  }

  @media ${device.laptopL} { 
    ${maxSize.laptopL};
  }

  @media ${device.desktop} { 
    ${maxSize.desktop};
  }
 
`;